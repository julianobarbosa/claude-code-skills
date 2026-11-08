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
    /// Open a pull request (GitHub: create, then labels and reviewers; Azure: link an existing work item)
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
        }),
        Command::Snapshot { message, daily, name, push } => {
            ship::snapshot::run(&message, daily, name.as_deref(), push)
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
