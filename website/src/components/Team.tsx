import React from "react";

export const Team = (props:any) => {
  return (
    <div id="team" className="text-center">
      <div className="container">
        <div className="col-md-8 col-md-offset-2 section-title">
          <h2>Meet the Team</h2>
          <p>
            The team is formed by Postdoc, Phd students and master student from dlab of EPFL
          </p>
        </div>
        <div id="row">
          {props.data
            ? props.data.map((d:any, i:any) => (
                <div key={`${d.name}-${i}`} className="col-md-4 col-sm-3 team">
                  <div className="thumbnail">
                    {" "}
                    <img src={d.img} alt="..." className="team-img" />
                    <div className="caption">
                      <h4>{d.name}</h4>
                      <p>{d.job}</p>
                    </div>
                  </div>
                </div>
              ))
            : "loading"}
        </div>
      </div>
    </div>
  );
};
