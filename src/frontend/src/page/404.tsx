import Container from "@/templates/Container";
import Panel from "@/templates/Panel";

interface Props {
  message?: string;
}

export default function FourZeroFour({ message }: Props) {
  return (
    <>
      <title>404</title>
      <Container>
      <Panel>
          <h1>404</h1>
          <p>Page not Found</p>
          <Panel type="inset-lighter">
            <p>{message}</p>
        </Panel>
      </Panel>
      </Container>
    </>
  );
}