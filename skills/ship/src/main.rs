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
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let result = match cli.command {
        Command::Detect { remote } => ship::detect::run(&remote).map(|()| 0),
        Command::Preflight { remote: _ } => ship::preflight::run().map(|()| 0),
        Command::Push { remote, branch } => ship::push::run(&remote, branch.as_deref()),
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
