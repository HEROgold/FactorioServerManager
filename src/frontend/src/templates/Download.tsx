import { DownloadForm } from "@/forms/Download";
import NoScript from "./noscript";
import Panel from "./Panel";

function Test() {
  return <>
    < h2 > Downloads</h2>
    <Panel type="inset-lighter">
      <p>Refer to the <a href="https://wiki.factorio.com/Download_API">Download Wiki</a> for more information on each dropdown</p>
      <p>Downloading will pause the website for the duration of the download!</p>
      <DownloadForm />
    </Panel>
  </>
}


export default function Download() {
  const categories: string[] = [];

  return <>
    <title>Dashboard</title>
    <NoScript />
    <div className="container-inner">
      <div id="flashed-messages" className="small-center"></div>
      <div className="medium-center">
        <div className="panel mb64 pb0">
          {categories.map(
            (category) => (
              <Test />
            )
          )}
        </div>
      </div>
    </div >

  </>
}