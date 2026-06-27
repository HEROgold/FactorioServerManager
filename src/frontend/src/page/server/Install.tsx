import Layout from "@/templates/Layout"
import NoScript from "../../components/NoScript"
import InstallForm from "@/forms/Install"
import { AvailableVersionProvider } from "@/contexts/AvailableVersion"


export default function Install() {
  return <>
    <AvailableVersionProvider>
      <Layout title="Install Server">
        <div className="container-inner">
          <div id="flashed-messages" className="small-center"></div>
          <NoScript />
          <div className="medium-center">
            <div className="panel mb64 pb0 m0 flex flex-grow flex-column">
              <h2>Server Manager</h2>
              <div className="panel-inset-lighter mb12">
                <h3>Install</h3>
                <InstallForm />
              </div>
            </div>
          </div>
        </div>
      </Layout>
    </AvailableVersionProvider>
  </>
}