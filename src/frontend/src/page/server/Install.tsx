import Layout from "../../templates/Layout";
import NoScript from "../../components/NoScript";
import InstallFormAPI from "../../forms/InstallAPI";
import { useAuth } from "../../hooks/useAuth";
import { useNavigate } from "react-router-dom";
import { useEffect } from "react";

export default function Install() {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, isLoading, navigate]);

  if (isLoading) {
    return (
      <Layout>
        <div className="container-inner">
          <div className="medium-center">
            <div className="panel mb64 pb0 m0 flex grow flex-column">
              <h2>Server Manager</h2>
              <p>Loading...</p>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="container-inner">
        <div id="flashed-messages" className="small-center"></div>
        <NoScript />
        <div className="medium-center">
          <div className="panel mb64 pb0 m0 flex grow flex-column">
            <h2>Create New Server</h2>
            <div className="panel-inset-lighter mb12 p12">
              <h3>Server Configuration</h3>
              <InstallFormAPI />
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}