describe("Coptic Translation & Linguistic Flow", () => {
  beforeEach(() => {
    cy.mockDialects();
    cy.visit("/translate");
  });

  it("renders translation interface and loads available dialects", () => {
    cy.wait("@getDialects");
    cy.get("h1").should("contain.text", "اكتب كلمة أو جملة عربية");
    cy.get("textarea.arabic-input").should("be.visible");
    cy.get("select").should("be.visible").find("option").should("have.length.at.least", 2);
    cy.get("button.translate-button").should("be.visible").and("contain.text", "ترجم");
  });

  it("validates empty input before submission", () => {
    cy.get("button.translate-button").click();
    cy.get("p.error").should("be.visible").and("contain.text", "اكتب كلمة أو جملة عربية أولًا");
  });

  it("translates an Arabic sentence into Coptic with linguistic breakdown", () => {
    cy.mockTranslation("translation_sentence.json");

    cy.get("textarea.arabic-input").type("الله محبة");
    cy.get("button.translate-button").click();

    cy.wait("@postTranslate").its("request.body").should("deep.include", {
      text: "الله محبة"
    });

    // Check translated Coptic title
    cy.get(".result-card").should("be.visible");
    cy.get(".coptic-title").should("contain.text", "ⲫⲛⲟⲩϯ ⲟⲩⲁⲅⲁⲡⲏ ⲡⲉ");

    // Check confidence score
    cy.get(".confidence-widget").should("contain.text", "95%");

    // Check word results
    cy.get(".result-card").should("contain.text", "ⲫⲛⲟⲩϯ");
    cy.get(".result-card").should("contain.text", "ⲁⲅⲁⲡⲏ");

    // Check grammar rules
    cy.get(".result-card").should("contain.text", "رابط الكينونة الاسمي المذكر");

    // Check save action
    cy.get(".result-actions button").first().should("contain.text", "احفظ النتيجة").click();
    cy.get(".result-actions button").first().should("contain.text", "تم الحفظ");
  });

  it("allows switching dialects (e.g. Sahidic vs Bohairic)", () => {
    cy.wait("@getDialects");
    cy.get("select").select("2"); // Select Sahidic
    cy.get("select").should("have.value", "2");
  });
});
