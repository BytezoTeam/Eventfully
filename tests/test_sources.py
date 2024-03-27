import pytest

import eventfully.database as db
from eventfully.sources.main import process_raw_event


@pytest.mark.parametrize(
    "raw_event,expected",
    [
        (
            db.RawEvent(
                raw="",
                title="OpenSunday Aemtler",
                description="IdéeSport öffnet während der Wintermonate am Sonntagnachmittag Sporthallen und bietet kostenlosen Raum für Bewegung und Begegnung. Die Kinder können die Veranstaltungen in der Sporthalle ohne Anmeldung besuchen. Kinder im Primarschulalter, mit und ohne Behinderungen: - entdecken vielfältige Bewegungserfahrungen und haben Freude am freien Spiel, treten mit unterschiedlichsten Kindern in Kontakt, reduzieren Berührungsängste und wählen selbstbestimmt ihre Aktivitäten.",
                link="https://www.ideesport.ch/projekte/opensunday-aemtler-a/",
                start_date="Sonntag 25. Februar 2024 13:30 - 16:30",
                end_date="Sonntag 25. Februar 2024 13:30 - 16:30",
                address="OpenSunday Aemtler, Turnhalle Aemtler C Aemtlerstrasse 101 CH-8003 Zürich",
            ),
            {
                "title": "OpenSunday Aemtler",
                "tags": ["sports"],
                "start_date": 1708864200,
                "link": "https://www.ideesport.ch/projekte/opensunday-aemtler-a/",
            },
        ),
        (
            db.RawEvent(
                raw="Gemeinsam die Zukunft formen Was denkst du über Gentechnik? Sollte wir sie benutzen um unsere Agrarprodukte ertragreicher und resistenter zu machen? Oder würden wir es in 10 Jahren bereuen? Es würde uns freuen, wenn du am 27.03, dabei bist bei unserem interaktiven workshop zu diesem Thema. Wir haben ein spezielles Format entwickelt, dass dir helfen wird, die “Grüne Gentechnik” aus allen Blickwinkeln zu verstehen und gleichzeitig Spass macht! Gäste - Prof. Beat Keller, Institut für Pflanzen- und Mikrobiologie, Universität Zürich - Dr. Monika Messmer, Departement für Nutzpflanzenwissenschaften, Forschungsinstitut für biologischen Landbau Wir wollen deine Meinung hören!\n27\n03\n24",
                title="GRUSELIGE GRÜNE GENTECHNIK?",
                description="Gemeinsam die Zukunft formen Was denkst du über Gentechnik? Sollte wir sie benutzen um unsere Agrarprodukte ertragreicher und resistenter zu machen? Oder würden wir es in 10 Jahren bereuen? Es würde uns freuen, wenn du am 27.03, dabei bist bei unserem interaktiven workshop zu diesem Thema. Wir haben ein spezielles Format entwickelt, dass dir helfen wird, die “Grüne Gentechnik” aus allen Blickwinkeln zu verstehen und gleichzeitig Spass macht! Gäste - Prof. Beat Keller, Institut für Pflanzen- und Mikrobiologie, Universität Zürich - Dr. Monika Messmer, Departement für Nutzpflanzenwissenschaften, Forschungsinstitut für biologischen Landbau Wir wollen deine Meinung hören!\n27\n03\n24",
                link="https://www.ccopy.org/dialog2-0-genomics-ch",
                start_date="Mittwoch 27. März 2024\n19:00 - 20:30",
                end_date="Mittwoch 27. März 2024\n19:00 - 20:30",
                address="Paulus Akademie\nPfingstweidstrasse 28\nCH-8005 Zürich",
                city="Zürich",
            ),
            {"tags": ["science"]},
        ),
        (
            db.RawEvent(
                raw="Gemeinsam entdecken wir das Quartier aus unterschiedlichen Perspektiven. Am 3. April besuchen wir gemeinsam langjährige Gewerbebetriebe in Wiedikon, die sich und ihre Geschichte vorstellen. Damit wollen wir Wiedikon aus der Sicht von unterschiedlichen Betrieben besser kennen lernen, verschiedene Perspektiven sichtbar machen und miteinander verknüpfen. Kommst du auch mit? Wir freuen uns dich auf dem Spaziergang kennen zu lernen, gemeinsam den Geschichten der Betriebe zu lauschen und vielleicht entdeckst du ja auch einen neuen Ort zum verweilen. Hast du Lust deine eigene Geschichte aus Wiedikon zu erzählen, dann melde dich bei uns. Wir organisieren gerne zusammen mit dir einen weiteren Quartierspaziergang zum Thema Wiedikon aus Sicht von… Kostenlos und ohne Anmeldung\n03\n04\n24",
                title="Wiedikon aus Sicht von...",
                description="Gemeinsam entdecken wir das Quartier aus unterschiedlichen Perspektiven. Am 3. April besuchen wir gemeinsam langjährige Gewerbebetriebe in Wiedikon, die sich und ihre Geschichte vorstellen. Damit wollen wir Wiedikon aus der Sicht von unterschiedlichen Betrieben besser kennen lernen, verschiedene Perspektiven sichtbar machen und miteinander verknüpfen. Kommst du auch mit? Wir freuen uns dich auf dem Spaziergang kennen zu lernen, gemeinsam den Geschichten der Betriebe zu lauschen und vielleicht entdeckst du ja auch einen neuen Ort zum verweilen. Hast du Lust deine eigene Geschichte aus Wiedikon zu erzählen, dann melde dich bei uns. Wir organisieren gerne zusammen mit dir einen weiteren Quartierspaziergang zum Thema Wiedikon aus Sicht von… Kostenlos und ohne Anmeldung\n03\n04\n24",
                link="https://gz-zh.ch/gz-heuried/programm/?standorte=7",
                start_date="Mittwoch 3. April 2024\n17:00 - 18:30",
                end_date="Mittwoch 3. April 2024\n17:00 - 18:30",
                address="Beim Spielwagen auf der Kollerwiese\nKollerwiese\nCH-8003 Zürich",
                city="Zürich",
            )
            ,
            {
                "tags": ["other"]
            }
        ),
    ],
)
def test_process_raw_event(raw_event: db.RawEvent, expected: dict):
    prompt_path = "../eventfully/sources/prompts.json"
    event = process_raw_event(raw_event, prompt_path)

    for key, value in expected.items():
        assert getattr(event, key) == value
