import styles from "./App.module.css";

/** Placeholder shell. Router, providers and layout arrive with the web scaffold issue (#18). */
export function App() {
  return (
    <main className={styles.shell}>
      <h1 className={styles.title}>3d-scan</h1>
      <p className={styles.tagline}>Scan an object. Get a print-ready 3MF for Bambu Studio.</p>
    </main>
  );
}
