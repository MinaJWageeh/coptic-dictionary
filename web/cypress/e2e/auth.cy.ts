describe("Authentication & Route Protection", () => {
  beforeEach(() => {
    cy.clearLocalStorage();
  });

  it("renders login page with credentials form", () => {
    cy.visit("/login");
    cy.get("h2").should("contain.text", "تسجيل الدخول");
    cy.get("input[type='email'], input[name='email']").should("be.visible");
    cy.get("input[type='password'], input[name='password']").should("be.visible");
    cy.get("button[type='submit']").should("contain.text", "دخول");
  });

  it("authenticates admin user and redirects to admin dashboard", () => {
    cy.intercept("POST", "**/auth/login*", {
      statusCode: 200,
      body: {
        access_token: "mock-valid-cypress-jwt-token",
        token_type: "bearer"
      }
    }).as("postLogin");

    cy.visit("/login");
    cy.get("input[type='email'], input[name='email']").clear().type("admin@coptic-dic.local");
    cy.get("input[type='password'], input[name='password']").clear().type("SecretPassword123!");
    cy.get("button[type='submit']").click();

    cy.wait("@postLogin");
    cy.url().should("include", "/admin");
  });

  it("redirects unauthenticated users trying to access protected routes", () => {
    cy.visit("/admin");
    cy.url().should("include", "/login");
  });
});
