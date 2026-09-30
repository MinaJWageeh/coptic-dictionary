import React from "react";
import RootLayout from "./app/_layout";

/**
 * Root App component fallback.
 * Primary routing is managed by Expo Router via `app/_layout.tsx` (main: "expo-router/entry").
 * This component provides a clean standalone fallback for test and tooling environments.
 */
export default function App() {
  return <RootLayout />;
}
