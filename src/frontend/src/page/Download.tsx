import { DownloadForm } from "@/forms/Download";
import Layout from "../templates/Layout";
import Panel from "../templates/Panel";
import { AvailableVersionProvider } from "@/contexts/AvailableVersion";

export default function Download() {
  return (
    <>
      <title>Downloads</title>
      <AvailableVersionProvider>
        <Layout title="Downloads">
          <div className="container-inner">
            <div id="flashed-messages" className="small-center"></div>
            <div className="medium-center">
              <div className="panel mb64 pb0">
                <h2>Downloads</h2>
                <Panel type="inset-lighter">
                  <p>
                    Refer to the <a href="https://wiki.factorio.com/Download_API">Download Wiki</a> for
                    more information on each version.
                  </p>
                  <DownloadForm />
                </Panel>
              </div>
            </div>
          </div>
        </Layout>
      </AvailableVersionProvider>
    </>
  );
}
