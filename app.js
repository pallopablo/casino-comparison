"use strict";


/* =========================================================
   ELEMENTS
========================================================= */

const tableBody =
    document.getElementById("casino-table-body");

const tableWrapper =
    document.getElementById("table-wrapper");

const loadingElement =
    document.getElementById("loading");

const errorElement =
    document.getElementById("error-message");

const offerCount =
    document.getElementById("offer-count");

const dataMeta =
    document.getElementById("data-meta");

const sourceName =
    document.getElementById("source-name");

const generatedDate =
    document.getElementById("generated-date");


/* =========================================================
   SECURITY HELPERS
========================================================= */

/*
    Only allow normal HTTP/HTTPS source links.

    This prevents unexpected URL protocols from being
    inserted into the page.
*/

function isSafeUrl(value) {

    try {

        const url = new URL(value);

        return (
            url.protocol === "http:" ||
            url.protocol === "https:"
        );

    } catch {

        return false;
    }
}


/* =========================================================
   FORMAT WAGERING REQUIREMENT
========================================================= */

function formatWagering(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {

        return {
            text: "Not stated",
            missing: true
        };
    }


    const number = Number(value);


    if (!Number.isFinite(number)) {

        return {
            text: "Not stated",
            missing: true
        };
    }


    return {
        text: `${number}x`,
        missing: false
    };
}


/* =========================================================
   FORMAT DATE
========================================================= */

function formatGeneratedDate(value) {

    if (!value) {
        return "Not available";
    }


    const date = new Date(value);


    if (Number.isNaN(date.getTime())) {
        return "Not available";
    }


    return date.toLocaleString();
}


/* =========================================================
   CREATE TABLE ROW
========================================================= */

function createCasinoRow(casino) {

    const row =
        document.createElement("tr");


    /* -----------------------------------------------------
       CASINO
    ----------------------------------------------------- */

    const casinoCell =
        document.createElement("td");

    casinoCell.textContent =
        casino.casino || "Not stated";


    /* -----------------------------------------------------
       WELCOME BONUS
    ----------------------------------------------------- */

    const bonusCell =
        document.createElement("td");

    bonusCell.textContent =
        casino.welcome_bonus || "Not stated";


    /* -----------------------------------------------------
       WAGERING REQUIREMENT
    ----------------------------------------------------- */

    const wageringCell =
        document.createElement("td");

    const wagering =
        formatWagering(
            casino.wagering_requirement
        );

    wageringCell.textContent =
        wagering.text;

    wageringCell.classList.add(
        "wagering-value"
    );


    if (wagering.missing) {

        wageringCell.classList.add(
            "not-stated"
        );
    }


    /* -----------------------------------------------------
       MINIMUM DEPOSIT
    ----------------------------------------------------- */

    const depositCell =
        document.createElement("td");

    depositCell.textContent =
        casino.minimum_deposit ||
        "Not stated";


    /* -----------------------------------------------------
       SOURCE URL
    ----------------------------------------------------- */

    const sourceCell =
        document.createElement("td");


    if (isSafeUrl(casino.source_url)) {

        const link =
            document.createElement("a");

        link.href =
            casino.source_url;

        link.textContent =
            "View source";

        link.className =
            "source-link";

        link.target =
            "_blank";

        link.rel =
            "noopener noreferrer";

        link.setAttribute(
            "aria-label",
            `View source for ${
                casino.casino || "casino"
            }`
        );

        sourceCell.appendChild(
            link
        );

    } else {

        sourceCell.textContent =
            "Unavailable";
    }


    /* -----------------------------------------------------
       ADD CELLS
    ----------------------------------------------------- */

    row.appendChild(
        casinoCell
    );

    row.appendChild(
        bonusCell
    );

    row.appendChild(
        wageringCell
    );

    row.appendChild(
        depositCell
    );

    row.appendChild(
        sourceCell
    );


    return row;
}


/* =========================================================
   VALIDATE JSON
========================================================= */

function validateCasinoData(data) {

    if (
        !data ||
        typeof data !== "object"
    ) {

        throw new Error(
            "The casino data file is invalid."
        );
    }


    if (!Array.isArray(data.casinos)) {

        throw new Error(
            "The casino list is missing."
        );
    }


    /*
        Assessment requirement:
        exactly three casinos.
    */

    if (data.casinos.length !== 3) {

        throw new Error(
            `Expected exactly 3 casinos, but found ${
                data.casinos.length
            }.`
        );
    }


    return true;
}


/* =========================================================
   DISPLAY DATA
========================================================= */

function displayCasinoData(data) {

    validateCasinoData(data);


    /*
        Clear anything that may already be in the table.
    */

    tableBody.replaceChildren();


    /*
        Generate the table directly from casinos.json.
    */

    data.casinos.forEach(
        (casino) => {

            const row =
                createCasinoRow(casino);

            tableBody.appendChild(
                row
            );
        }
    );


    /*
        Update count.
    */

    offerCount.textContent =
        `${data.casinos.length} offers loaded`;


    /*
        Update metadata.
    */

    sourceName.textContent =
        data.source_name ||
        "Not available";


    generatedDate.textContent =
        formatGeneratedDate(
            data.generated_at_utc
        );


    /*
        Hide loading message.
    */

    loadingElement.classList.add(
        "hidden"
    );


    /*
        Show table and metadata.
    */

    tableWrapper.classList.remove(
        "hidden"
    );

    dataMeta.classList.remove(
        "hidden"
    );
}


/* =========================================================
   DISPLAY ERROR
========================================================= */

function displayError(error) {

    console.error(
        "Casino data error:",
        error
    );


    loadingElement.classList.add(
        "hidden"
    );


    tableWrapper.classList.add(
        "hidden"
    );


    dataMeta.classList.add(
        "hidden"
    );


    offerCount.textContent =
        "Unable to load offers";


    errorElement.textContent =
        "The casino data could not be loaded. " +
        "Make sure casinos.json exists and that " +
        "the website is being opened through a " +
        "local or hosted web server.";


    errorElement.classList.remove(
        "hidden"
    );
}


/* =========================================================
   LOAD casinos.json
========================================================= */

async function loadCasinoData() {

    try {

        /*
            Prevent the browser from relying on an old
            cached version while testing fresh scraper data.
        */

        const response = await fetch(
            "./casinos.json",
            {
                cache: "no-store"
            }
        );


        if (!response.ok) {

            throw new Error(
                `HTTP ${response.status}`
            );
        }


        const data =
            await response.json();


        displayCasinoData(
            data
        );

    } catch (error) {

        displayError(
            error
        );
    }
}


/* =========================================================
   START APPLICATION
========================================================= */

loadCasinoData();