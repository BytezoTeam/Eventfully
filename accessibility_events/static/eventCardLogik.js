// This is a comment, which is a valid JavaScript expression.
import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import {
  faEuroSign,
  faMapPin,
  faCalendarAlt,
  faTags,
  faGlobe,
} from "@fortawesome/free-solid-svg-icons";

function EventCard() {
  return (
    <div>
      <h2>Event Titel</h2>
      <p>Event Beschreibung</p>
      <footer>
        <div>
          <FontAwesomeIcon icon={faEuroSign} />
          Event Preis <br />
          <FontAwesomeIcon icon={faMapPin} />
          Event Ort <br />
          <FontAwesomeIcon icon={faCalendarAlt} />
          Event Startdatum <br />
          <FontAwesomeIcon icon={faTags} /> Event Themen <br />
          <FontAwesomeIcon icon={faGlobe} /> <a href="Event Link">Event Link</a>
        </div>
      </footer>
    </div>
  );
}

export default EventCard;
