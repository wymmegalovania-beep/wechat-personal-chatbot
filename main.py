import click
from dotenv import load_dotenv

from chatbot import PersonalChatbot
from data_processor import create_personal_profile


@click.command()
@click.option("--init", "init_file", type=click.Path(exists=True), help="Import chat file and build profile.")
@click.option("--user", "user_name", default=None, help="Your name in chat history.")
@click.option("--profile", "profile_path", default="personal_profile.json", show_default=True)
def cli(init_file, user_name, profile_path):
    load_dotenv()

    if init_file:
        profile = create_personal_profile(init_file, user_name=user_name, output_file=profile_path)
        click.echo(f"Profile initialized: {profile_path}")
        click.echo(f"Detected user: {profile['user_name']}")
        click.echo(f"Examples loaded: {len(profile['examples'])}")
        return

    bot = PersonalChatbot(profile_path=profile_path)
    click.echo("WeChat Personal Chatbot started. Type 'exit' to quit.")
    while True:
        user_input = click.prompt("You", prompt_suffix=" > ", type=str)
        if user_input.strip().lower() in {"exit", "quit"}:
            click.echo("Bye.")
            break
        if not user_input.strip():
            continue
        try:
            answer = bot.reply(user_input)
            click.echo(f"Bot > {answer}")
        except Exception as exc:
            click.echo(f"Error: {exc}")


if __name__ == "__main__":
    cli()
