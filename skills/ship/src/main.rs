use clap::{Parser, Subcommand};
use std::io::ErrorKind;
use std::process::ExitCode;

#[derive(Parser)]
#[command(name = "ship", version, about)]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
// Parsed once per process; boxing the `Pr` flags would only add indirection.
#[allow(clippy::large_enum_variant)]
enum Command {
    /// Print the delivery platform and coordinates for a remote, as key=value lines
    Detect {
        /// Git remote to inspect
        #[arg(default_value = "origin")]
        remote: String,
    },
    /// Check there is something to deliver and that no changed file is left out of scope
    Preflight {
        /// Accepted for parity with the TS script, which ignores it
        #[arg(value_name = "REMOTE", default_value = "origin")]
        remote: String,
    },
    /// Push the current branch and set upstream (Azure: az Bearer token first)
    Push {
        /// Git remote to push to
        #[arg(short, long, default_value = "origin")]
        remote: String,
        /// Branch to push (default: the current branch)
        #[arg(short, long)]
        branch: Option<String>,
    },
    /// Open a pull request (GitHub: create, then labels and reviewers; Azure: link or create work items)
    Pr {
        /// PR title (required)
        #[arg(long, allow_hyphen_values = true)]
        title: Option<String>,
        /// PR body
        #[arg(long, default_value = "", allow_hyphen_values = true)]
        body: String,
        /// Read the PR body from this file (wins over --body)
        #[arg(long, value_name = "FILE")]
        body_file: Option<String>,
        /// Branch the PR merges into
        #[arg(long, default_value = "main", allow_hyphen_values = true)]
        target: String,
        /// Branch the PR is opened from (default: the current branch)
        #[arg(long, allow_hyphen_values = true)]
        source: Option<String>,
        /// Git remote the PR is opened against
        #[arg(short, long, default_value = "origin", allow_hyphen_values = true)]
        remote: String,
        /// Open the PR as a draft
        #[arg(long)]
        draft: bool,
        /// Label(s), comma-separated and repeatable (default: derived from the title or branch)
        #[arg(long = "tag", value_name = "TAGS", allow_hyphen_values = true)]
        tags: Vec<String>,
        /// Add no labels
        #[arg(long)]
        no_tag: bool,
        /// Reviewer(s), comma-separated and repeatable
        #[arg(long = "reviewer", value_name = "LOGINS", allow_hyphen_values = true)]
        reviewers: Vec<String>,
        /// Required reviewer(s); GitHub has no per-PR required reviewer, so they are requested normally
        #[arg(long = "required-reviewer", value_name = "LOGINS", allow_hyphen_values = true)]
        required_reviewers: Vec<String>,
        /// Request no reviewers (Azure only; accepted for parity)
        #[arg(long)]
        no_reviewer: bool,
        /// Azure-only: work item(s) related to the PR; on GitHub this only prints a note
        #[arg(long = "related", value_name = "IDS", allow_hyphen_values = true)]
        related: Vec<String>,
        /// Azure-only: existing work item to link (default: the number in the branch name)
        #[arg(long, value_name = "ID", allow_hyphen_values = true)]
        work_item: Option<String>,
        /// Azure-only: never create a work item (the PR opens unlinked if none is found)
        #[arg(long)]
        no_create_work_item: bool,
        /// Azure-only: title of a work item to create (repeatable; one per task)
        #[arg(long = "task", value_name = "TITLE", allow_hyphen_values = true)]
        tasks: Vec<String>,
        /// Azure-only: file with one work-item title per line (appended after --task)
        #[arg(long, value_name = "FILE", allow_hyphen_values = true)]
        tasks_file: Option<String>,
        /// Azure-only: assignee of created work items (default: $SHIP_ADO_ASSIGNEE; empty = unassigned)
        #[arg(long, allow_hyphen_values = true)]
        assignee: Option<String>,
        /// Azure-only: type of created work items
        #[arg(long, default_value = "Task", allow_hyphen_values = true)]
        work_item_type: String,
        /// Azure-only: state to move each linked work item to after the PR opens (e.g. Resolved)
        #[arg(long, value_name = "STATE", allow_hyphen_values = true, overrides_with = "transition")]
        transition: Option<String>,
        /// Azure-only: leave "complete linked work items after merging" unticked on the PR
        #[arg(long, overrides_with = "no_complete_transition")]
        no_complete_transition: bool,
    },
    /// Add, remove or list the tags of an existing pull request (Azure tags, GitHub labels)
    Tag {
        /// Pull request id (Azure `pr_id`, GitHub `pr_number`); digits only
        #[arg(value_name = "ID")]
        id: Option<String>,
        /// Pull request id, as a flag
        #[arg(long = "pr", value_name = "ID", allow_hyphen_values = true, overrides_with = "pr")]
        pr: Option<String>,
        /// Tag(s) to add, comma-separated and repeatable
        #[arg(long = "add", value_name = "TAGS", allow_hyphen_values = true)]
        add: Vec<String>,
        /// Tag(s) to remove, comma-separated and repeatable
        #[arg(long = "remove", value_name = "TAGS", allow_hyphen_values = true)]
        remove: Vec<String>,
        /// Print the current tags (the default when nothing is added or removed)
        #[arg(long, overrides_with = "list")]
        list: bool,
        /// Git remote the PR belongs to
        #[arg(short, long, default_value = "origin", allow_hyphen_values = true, overrides_with = "remote")]
        remote: String,
    },
    /// Save HEAD as an annotated, self-describing git tag (a checkpoint)
    Snapshot {
        /// Extra message paragraph (repeatable; each becomes its own paragraph)
        #[arg(short, long = "message", value_name = "PARA", allow_hyphen_values = true)]
        message: Vec<String>,
        /// Name the tag v<YYYY.MM.DD> instead of v<YYYY.MM.DD-HHMM>
        #[arg(long)]
        daily: bool,
        /// Use this exact tag name, ignoring the date scheme
        #[arg(long, value_name = "TAG", allow_hyphen_values = true)]
        name: Option<String>,
        /// Push the tag to origin after creating it (Azure: az Bearer token first)
        #[arg(long)]
        push: bool,
    },
    /// Open a URL in the browser profile signed in with a chosen email
    Open {
        /// URL to open
        url: Option<String>,
        /// Open as this account
        #[arg(long, value_name = "EMAIL", allow_hyphen_values = true, overrides_with = "profile")]
        profile: Option<String>,
        /// Force a browser: edge or chrome
        #[arg(long, value_name = "BROWSER", allow_hyphen_values = true, overrides_with = "browser")]
        browser: Option<String>,
        /// Print the discovered email -> profile map and exit
        #[arg(long, overrides_with = "list_profiles")]
        list_profiles: bool,
        /// Remember this email (and --browser) as the default and exit
        #[arg(long, value_name = "EMAIL", allow_hyphen_values = true, overrides_with = "set_default")]
        set_default: Option<String>,
        /// Resolve and print the profile without launching a browser
        #[arg(long, overrides_with = "dry_run")]
        dry_run: bool,
    },
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let result = match cli.command {
        Command::Detect { remote } => ship::detect::run(&remote).map(|()| 0),
        Command::Preflight { remote: _ } => ship::preflight::run().map(|()| 0),
        Command::Push { remote, branch } => ship::push::run(&remote, branch.as_deref()),
        Command::Pr {
            title,
            body,
            body_file,
            target,
            source,
            remote,
            draft,
            tags,
            no_tag,
            reviewers,
            required_reviewers,
            no_reviewer,
            related,
            work_item,
            no_create_work_item,
            tasks,
            tasks_file,
            assignee,
            work_item_type,
            transition,
            no_complete_transition,
        } => ship::pr::run(&ship::pr::Args {
            title,
            body,
            body_file,
            target,
            source,
            remote,
            draft,
            tags,
            no_tag,
            reviewers,
            required_reviewers,
            no_reviewer,
            related,
            work_item,
            no_create_work_item,
            tasks,
            tasks_file,
            assignee,
            work_item_type,
            transition,
            no_complete_transition,
        }),
        Command::Tag { id, pr, add, remove, list, remote } => {
            ship::tag::run(&ship::tag::Args { id, pr, add, remove, list, remote })
        }
        Command::Snapshot { message, daily, name, push } => {
            ship::snapshot::run(&message, daily, name.as_deref(), push)
        }
        Command::Open { url, profile, browser, list_profiles, set_default, dry_run } => {
            ship::open::run(&ship::open::Args { url, profile, browser, list_profiles, set_default, dry_run })
        }
    };
    match result {
        Ok(0) => ExitCode::SUCCESS,
        Ok(code) => ExitCode::from(code),
        // A closed pipe (`ship detect | head -1`) is the reader's choice, not a failure.
        Err(e) if e.kind() == ErrorKind::BrokenPipe => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("ship: {e}");
            ExitCode::FAILURE
        }
    }
}
