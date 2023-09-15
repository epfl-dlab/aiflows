import React from "react";

export const Contribute = (props:any) => {
  return (
    <div id="contribute" className="text-center">
      <div className="container">
        <div className="section-title">
          <h2>Make Contributions to the project</h2>
          <p>
            The project is still under development, and all sorts of contributions are welcomed
          </p>
        </div>
        <div className="row">
          {props.data
            ? props.data.map((d:any, i:any) => (
                <div key={`${d.name}-${i}`} className="col-md-4">
                  {" "}
                  <i className={d.icon}></i>
                  <div className="service-desc">
                    <h3>{d.name}</h3>
                    <p>{d.text}</p>
                  </div>
                </div>
              ))
            : "loading"}
        </div>
      </div>
    </div>
  );
};
