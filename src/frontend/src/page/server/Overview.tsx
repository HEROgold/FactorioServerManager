import { Link } from "react-router-dom";
import Layout from "../../templates/Layout";

export interface Server {
  name: string
}

function ServerLink({ server }: { server: Server }) {
  return <Link to={`/server/${server.name}/index`}>{server.name}</Link>
}

export default function Overview() {
  const servers: Server[] = []
  const serverName = "FactorioServer"

  return <>
    <title>Dashboard</title>
    <Layout>
      <div className="container-inner">
        <div id="flashed-messages" className="small-center"></div>
        <div className="medium-center">
          <div className="panel mb64 pb0 m0 flex grow flex-column">
            <h2>Server Overview</h2>
            <div className="panel-inset-lighter mb12">
              <a href={`servers/${serverName}/create/`} className="button">Create Server</a>
              <div className="panel-inset-lighter mb12">
                <h3>Servers</h3>
                {servers.map(
                  (i) => (
                    <ServerLink server={i} />
                  )
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  </>
}