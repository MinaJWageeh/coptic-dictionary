describe("Saved Translations (Local Cache)", () => {
  it("displays empty state when no translations are saved", () => {
    cy.clearLocalStorage();
    cy.visit("/saved");
    cy.get("h1").should("contain.text", "الترجمات التي حفظتها");
    cy.get(".empty-state").should("contain.text", "لا توجد ترجمات محفوظة بعد");
  });

  it("lists saved translations from local storage and allows deletion", () => {
    const mockSavedItem = {
      id: "saved-test-1",
      createdAt: new Date().toISOString(),
      inputText: "الله محبة",
      dialectName: "البحيرية",
      result: {
        input_type: "sentence",
        status: "candidate_generated",
        translation: "ⲫⲛⲟⲩϯ ⲟⲩⲁⲅⲁⲡⲏ ⲡⲉ",
        confidence: 0.95
      }
    };

    cy.visit("/saved", {
      onBeforeLoad(win) {
        win.localStorage.setItem("coptic-web-saved-translations", JSON.stringify([mockSavedItem]));
      }
    });

    cy.get(".saved-item").should("have.length", 1);
    cy.get(".saved-item").should("contain.text", "الله محبة");
    cy.get(".saved-item").should("contain.text", "ⲫⲛⲟⲩϯ ⲟⲩⲁⲅⲁⲡⲏ ⲡⲉ");
    cy.get(".saved-item").should("contain.text", "95%");

    // Test Deletion
    cy.get(".saved-actions button.danger").click();
    cy.get(".empty-state").should("contain.text", "لا توجد ترجمات محفوظة بعد");
  });
});
