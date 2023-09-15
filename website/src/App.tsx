import React, { useState, useEffect } from "react";
import { Navigation } from "./components/navigation";
import { Header } from "./components/header";
import { Features } from "./components/features";
import { About } from "./components/about";
import { Contribute } from "./components/contribute";
import { Gallery } from "./components/gallery";
import { Testimonials } from "./components/testimonials";
import { Team } from "./components/Team";
import JsonData from "./data/data.json";
import SmoothScroll from "smooth-scroll";
import "./App.css";

export const scroll = new SmoothScroll('a[href*="#"]', {
  speed: 1000,
  speedAsDuration: true,
});

interface about_structure{
  paragraph: string;
  Why: object;
  Why2: object
}

interface Props {
  Header: object;
  Features: object;
  About: object;
  Gallery: object;
  Team: object;
  Contact: object;
  Contribute: object
}

const App = () => {

  const [landingPageData, setLandingPageData] = useState<Props>({
    Header: {},
    Features: [],
    About: {},
    Gallery: [],
    Team: [],
    Contact: {},
    Contribute: []
  });
  useEffect(() => {
    setLandingPageData(JsonData);
  }, []);

  return (
    <div>
      <Navigation />
      <Header data={landingPageData.Header} />
      <Features data={landingPageData.Features} />
      <About data={(landingPageData.About)} />
      <Gallery data={landingPageData.Gallery} />
      <Contribute data={landingPageData.Contribute} />

        {
            //<Team data={landingPageData.Team} />
            // <Contact data={landingPageData.Contact} />
        }

    </div>
  );
};

export default App;
