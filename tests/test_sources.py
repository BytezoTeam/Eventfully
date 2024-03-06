from eventfully.sources.main import process_field, process_raw_event
import eventfully.database as db


raw_event = db.RawEvent(
    raw="",
    title="OpenSunday Aemtler",
    description="IdéeSport öffnet während der Wintermonate am Sonntagnachmittag Sporthallen und bietet kostenlosen Raum für Bewegung und Begegnung. Die Kinder können die Veranstaltungen in der Sporthalle ohne Anmeldung besuchen. Kinder im Primarschulalter, mit und ohne Behinderungen: - entdecken vielfältige Bewegungserfahrungen und haben Freude am freien Spiel, treten mit unterschiedlichsten Kindern in Kontakt, reduzieren Berührungsängste und wählen selbstbestimmt ihre Aktivitäten.",
    link="https://www.ideesport.ch/projekte/opensunday-aemtler-a/",
    start_date="Sonntag 25. Februar 2024 13:30 - 16:30",
    end_date="Sonntag 25. Februar 2024 13:30 - 16:30",
    address="OpenSunday Aemtler, Turnhalle Aemtler C Aemtlerstrasse 101 CH-8003 Zürich",
)


def test_process_field():
    result = process_field(
        raw_event,
        "title",
        {"type": "string", "description": "The title of the event."},
        "Extract the following information from the given event data from the user."
    )
    assert result == "OpenSunday Aemtler"


def test_process_raw_event():
    process_raw_event(raw_event, "../eventfully/sources/prompts.json")
