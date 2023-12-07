import { Image } from "./image";
import React from "react";

export const GettingStarted = (props:any) => {
  return (
    <div id="getting_started" className="text-center">
      <div className="container">
        <div className="section-title">
          <h2>Getting Started</h2>
          <p>
            ToDo
          </p>
        </div>
        <div className="row">
          <div className="portfolio-items">
            {props.data
              ? props.data.map((d:any, i:any) => (
                  <div
                    key={`${d.title}-${i}`}
                    className="col-sm-6 col-md-4 col-lg-4"
                  >
                    <Image
                      title={d.title}
                      largeImage={d.largeImage}
                      smallImage={d.smallImage}
                    />
                  </div>
                ))
              : "Loading..."}
          </div>
        </div>
      </div>
    </div>
  );
};
