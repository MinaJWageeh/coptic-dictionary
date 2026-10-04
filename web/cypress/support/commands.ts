/// <reference types="cypress" />

declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Intercepts dialects API with mock fixture
       */
      mockDialects(): Chainable<void>;

      /**
       * Intercepts translation API with custom or fixture data
       */
      mockTranslation(fixtureOrData?: string | object): Chainable<void>;

      /**
       * Intercepts dictionary browse API
       */
      mockDictionaryBrowse(fixtureOrData?: string | object): Chainable<void>;

      /**
       * Sets mock admin session in localStorage
       */
      loginAsAdmin(): Chainable<void>;
    }
  }
}

Cypress.Commands.add("mockDialects", () => {
  cy.intercept("GET", "**/dialects*", {
    statusCode: 200,
    body: [
      { id: 1, code: "Bohairic", name: "Bohairic", name_ar: "بحيري" },
      { id: 2, code: "Sahidic", name: "Sahidic", name_ar: "صعيدي" },
      { id: 3, code: "Akhmimic", name: "Akhmimic", name_ar: "أخميمي" }
    ]
  }).as("getDialects");
});

Cypress.Commands.add("mockTranslation", (fixtureOrData = "translation_sentence.json") => {
  if (typeof fixtureOrData === "string") {
    cy.intercept("POST", "**/translate*", { fixture: fixtureOrData }).as("postTranslate");
  } else {
    cy.intercept("POST", "**/translate*", { statusCode: 200, body: fixtureOrData }).as("postTranslate");
  }
});

Cypress.Commands.add("mockDictionaryBrowse", (fixtureOrData = "dictionary_browse.json") => {
  if (typeof fixtureOrData === "string") {
    cy.intercept("GET", "**/dictionary/browse*", { fixture: fixtureOrData }).as("getDictionaryBrowse");
  } else {
    cy.intercept("GET", "**/dictionary/browse*", { statusCode: 200, body: fixtureOrData }).as("getDictionaryBrowse");
  }
});

Cypress.Commands.add("loginAsAdmin", () => {
  const session = {
    token: "mock-jwt-test-token-cypress",
    user: {
      id: 1,
      email: "admin@coptic-dic.local",
      username: "admin",
      role: "admin"
    }
  };
  window.localStorage.setItem("coptic_dic_session", JSON.stringify(session));
});

export {};
