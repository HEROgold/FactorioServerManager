import { Link, useNavigate, useParams } from "react-router-dom"
import Layout from "../../templates/Layout"
import StatusBox from "@/components/StatusBox";
import ManageServerForm from "@/forms/Settings";


async function fetchDelete(url: string) {
  return await fetch(url, {
    method: 'DELETE',
  });
}

function DeleteButton({ name }: { name: string }) {
  const handleClick = async (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();

    if (confirm(`Are you sure you want to delete ${name}?`)) {
      const response = await fetchDelete(`/server/${name}`)

      if (response.ok) {
        window.location.href = e.currentTarget.href;
      } else {
        alert('Delete failed');
      }
    }
  };

  return <>
    <Link
      className="button button-red"
      to={"/server/dashboard"}
      onClick={handleClick}
    >
      Delete Server
    </Link>
  </>
}


export default function Manage() {
  const { name } = useParams()

  if (name === undefined) {
    const navigate = useNavigate()
    navigate("/server/dashboard")
    return
  }

  return <>
    <title>{name}</title>
    <Layout>
      <div className="container-inner">
        <div id="flashed-messages" className="small-center"></div>
        <div className="medium-center">
          <div className="panel mb64 pb0 m0 flex grow flex-column">
            <h2>{name}</h2>
            <div className="server-subnav">
              <a className="button button-ghost" href={`/servers/${name}/mods`}>Open Mod Manager</a>
            </div>
            <DeleteButton name={name} />
            <div className="panel-inset-lighter mb12">
              <StatusBox />
              <br />
              <ManageServerForm />
            </div>
          </div>
        </div>
      </div>

    </Layout>
  </>
}