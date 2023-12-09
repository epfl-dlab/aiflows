import React from "react";


export const Image = ({ title, src }:{title:any, src:any}) => {
  return (
      <img src={src} className="img-responsive logo" alt={title} />
  );
};

export const Navigation = (props:any) => {
  return (
    <nav id="menu" className="navbar navbar-default navbar-fixed-top">
      <div style={{marginInline:"10px"}}>
        <div className="navbar-header">
          <button
            type="button"
            className="navbar-toggle collapsed"
            data-toggle="collapse"
            data-target="#bs-example-navbar-collapse-1"
          >
            {" "}
            <span className="sr-only">Toggle navigation</span>{" "}
            <span className="icon-bar"></span>{" "}
            <span className="icon-bar"></span>{" "}
            <span className="icon-bar"></span>{" "}
          </button>
          <a className="navbar-brand page-scroll" href="#page-top">
            <Image src="assets/flows_logo_nav.png" title="logo" />
          </a>{" "}
        </div>

        <div
          className="collapse navbar-collapse"
          id="bs-example-navbar-collapse-1"
        >
          <ul className="nav navbar-nav navbar-right">
            <li>
              <a href="#features" className="page-scroll">
                Features
              </a>
            </li>
            <li>
              <a href="#getting_started" className="page-scroll">
                Examples
              </a>
            </li>
            <li>
              <a href="#contribute" className="page-scroll">
                Join us
              </a>
            </li>
            <li>
              <a href="docs/built_with_sphinx/html/getting_started/index.html" className="page-scroll">
                Getting Started
              </a>
            </li>
            <li>
              <a href="docs/built_with_sphinx/html/index.html" className="page-scroll">
                Docs
              </a>
            </li>
            <li>
                <a href="https://github.com/epfl-dlab/aiflows" style={{position:'relative', top:'-5'}}>
                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor"

                       className="bi bi-github" viewBox="0 0 16 16">
                    <path
                        d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.012 8.012 0 0 0 16 8c0-4.42-3.58-8-8-8z"/>
                  </svg>
                </a>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  );
};
