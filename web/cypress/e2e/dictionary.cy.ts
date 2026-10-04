describe("Coptic Dictionary Browse & Search", () => {
  beforeEach(() => {
    cy.mockDialects();
    cy.mockDictionaryBrowse("dictionary_browse.json");
    cy.visit("/dictionary");
  });

  it("renders dictionary browse page with search bar and alphabet bar", () => {
    cy.wait("@getDialects");
    cy.wait("@getDictionaryBrowse");

    cy.get("h1").should("contain.text", "تصفح وابحث في مفردات اللغة القبطية");
    cy.get(".search-box input").should("be.visible");
    cy.get("select").should("have.length.at.least", 2);
  });

  it("displays dictionary entries with Coptic lemmas and Arabic meanings", () => {
    cy.wait("@getDictionaryBrowse");

    cy.get(".dictionary-item").should("have.length", 2);

    // Entry 1: agape
    cy.get(".dictionary-item").first().within(() => {
      cy.get(".coptic-word").should("contain.text", "ⲁⲅⲁⲡⲏ");
      cy.contains("محبة").should("be.visible");
      cy.contains("Crum Coptic Dictionary").should("be.visible");
    });

    // Entry 2: nouti
    cy.get(".dictionary-item").eq(1).within(() => {
      cy.get(".coptic-word").should("contain.text", "ⲛⲟⲩϯ");
      cy.contains("الله").should("be.visible");
    });
  });

  it("triggers search query when typing into search box", () => {
    cy.intercept("GET", "**/dictionary/browse?*q=%D9%85%D8%AD%D8%A8%D8%A9*", {
      fixture: "dictionary_browse.json"
    }).as("searchQuery");

    cy.get(".search-box input").type("محبة");
    cy.wait("@searchQuery");
  });
});
