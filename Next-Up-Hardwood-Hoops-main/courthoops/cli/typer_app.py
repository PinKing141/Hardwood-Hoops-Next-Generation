import typer

from courthoops.infra.persistence.orm.models import Base
from courthoops.infra.persistence.orm.session import make_session_factory
from courthoops.infra.persistence.repositories.save_slot_repository import SaveSlotRepository
from courthoops.infra.utils.db_admin import migrate_sqlite_universe_columns, sqlite_path_from_url

app = typer.Typer(help="Typer-based admin/utility CLI. Use legacy CLI for full sims.")


def _session_factory_from_db(db_path: str):
    url = db_path if "://" in db_path else f"sqlite:///{db_path}"
    return url, make_session_factory(url, Base.metadata)


@app.command("migrate-db")
def migrate_db(db_path: str = typer.Option("courthoops.db", help="SQLite DB path or URL.")) -> None:
    """Add universe_id columns and save_slots table to an existing SQLite DB."""
    url = db_path if "://" in db_path else f"sqlite:///{db_path}"
    sqlite_path = sqlite_path_from_url(url)
    migrate_sqlite_universe_columns(sqlite_path)
    typer.echo(f"Migrated DB at {sqlite_path}")


@app.command("list-saves")
def list_saves(db_path: str = typer.Option("courthoops.db", help="SQLite DB path or URL.")) -> None:
    """List all save slots with their universes/worlds."""
    url, session_factory = _session_factory_from_db(db_path)
    repo = SaveSlotRepository(session_factory)
    slots = repo.list_all()
    if not slots:
        typer.echo("No save slots found.")
        return
    for slot in slots:
        typer.echo(
            f"Save {slot.save_id} | universe={slot.universe_id} | world={slot.world_id} | "
            f"created={slot.created_at} | last_played={slot.last_played_at} | name={slot.name}"
        )


def main():
    app()


if __name__ == "__main__":
    main()
