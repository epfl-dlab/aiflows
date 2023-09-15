import { Image } from "./image";
import React from "react";

export const Gallery = (props:any) => {
  return (
    <div id="portfolio" className="text-center">
      <div className="container">
        <div className="section-title">
          <h2>Gallery</h2>
          <p>
            We have used our Flows library to create AI agents that can participate in competitive coding challenges.
            But this is just the beginning.
            With the Flow-verse we prepare a new paradigm of sharing and collaborating on next-generation AI agents.
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
