import React from "react";

export const Contribute = (props:any) => {
  return (
    <div id="contribute" className="text-center">
      <div className="container">
        <div className="section-title">
          <h2>Join us!</h2>
          <p>
            aiFlows aims to become a community driven project that will empower both researchers and practitioners, and it is just getting started. Let's work on a great (open-source) AI future, together! Join us on <a href="https://discord.gg/yFZkpD2HAh" style={{"color": "white"}}><u><b>Discord</b></u></a>!
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
