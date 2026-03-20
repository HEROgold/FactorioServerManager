import Layout from "../templates/Layout";

export const HomePage = () => {
  return (
    <Layout title="Home - Factorio Style">
      <h1>Welkom op de pagina</h1>
      <button hx-get="/api/data">Htmx actie</button>
    </Layout>
  );
};
