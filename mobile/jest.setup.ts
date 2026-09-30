import "@testing-library/jest-native/extend-expect";

jest.mock("@react-native-async-storage/async-storage", () =>
  require("@react-native-async-storage/async-storage/jest/async-storage-mock")
);

jest.mock("expo-router", () => ({
  Link: ({ children }: { children: React.ReactNode }) => children,
  Stack: () => null,
  router: { push: jest.fn(), replace: jest.fn() },
  usePathname: () => "/",
  useFocusEffect: (callback: () => void | (() => void)) => callback()
}));
