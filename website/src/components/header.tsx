import React from "react";
import {faCopy} from "@fortawesome/free-regular-svg-icons";
import {FontAwesomeIcon} from "@fortawesome/react-fontawesome";

export const Image = ({ title, src }:{title:any, src:any}) => {
  return (
      <img src={src} className="img-responsive header-logo" alt={title} />
  );
};

export const Header = (props: any) => {
    return (
        <header id="header">
            <div className="intro">
                <div className="overlay">
                    <div className="container">
                        <div className="row">
                            <div className="col-md-8 col-md-offset-2 intro-text">
                                <Image src="assets/flows_logo_header.png" title="logo" />

                                <div style={{height: "70px"}}>
                                    <div style={{
                                        paddingTop: "20px",
                                        borderRadius: "20px",
                                        width: "70%",
                                        position: "relative",
                                        left: "15%",
                                        marginTop: "35px",
                                        marginBottom: "20px",
                                        whiteSpace: "pre",
                                        textAlign: "left",
                                    }}><pre style={{
                                        position: "absolute",
                                        width: "100%",
                                        left: "0%",
                                        top: "0%",
                                        backgroundColor: props.data.codeBGColor,
                                        color: "#ffffff",
                                        borderColor: "#111111",
                                        borderRadius: "20px",
                                        fontSize: "20px",
                                    }}>{props.data.code}
                                </pre>

                                        <button style={{
                                            position: "absolute",
                                            left: "90%",
                                            top: "0%",
                                            backgroundColor: props.data.codeBGColor,
                                            color: "#ffffff",
                                            borderRadius: "20px",
                                            border: "none",
                                            padding: "10px",
                                            cursor: "pointer",
                                        }} onClick={() => {
                                            navigator.clipboard.writeText(props.data.code);
                                        }}>
                                            <FontAwesomeIcon color={"white"} size="2x" icon={faCopy}/>


                                        </button>

                                    </div>
                                </div>


<div style={{
  display: 'flex', // This makes the parent a flex container
  justifyContent: 'center', // This centers its children horizontally
  alignItems: 'center', // This centers its children vertically (if the parent has a defined height)
  height: '100%' // Set a height if you want vertical centering
}}>
  <div style={{
    width: "50%",
    display: 'flex',
    justifyContent: 'space-between' // This keeps the buttons spaced across the width of the container
  }}>
    <a
      href="#getting_started"
      className="btn btn-custom btn-lg page-scroll"
    >
      Flows in Action
    </a>
    <a
      href="https://github.com/epfl-dlab/aiflows"
      className="btn btn-custom btn-lg page-scroll"
    >
      Github
    </a>
  </div>
</div>

                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </header>
    )
        ;
};
