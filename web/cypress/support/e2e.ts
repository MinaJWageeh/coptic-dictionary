// ***********************************************************
// Cypress support/e2e.ts
// ***********************************************************

import "./commands";

// Prevent uncaught exceptions from failing tests if triggered by 3rd-party scripts or Next hydration
Cypress.on("uncaught:exception", (err) => {
  // Returning false here prevents Cypress from failing the test
  if (err.message.includes("NEXT_REDIRECT") || err.message.includes("Hydration")) {
    return false;
  }
  return true;
});
