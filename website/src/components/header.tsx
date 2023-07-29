import React from "react";
import {faCopy} from "@fortawesome/free-regular-svg-icons";
import {FontAwesomeIcon} from "@fortawesome/react-fontawesome";

export const Header = (props: any) => {
    return (
        <header id="header">
            <div className="intro">
                <div className="overlay">
                    <div className="container">
                        <div className="row">
                            <div className="col-md-8 col-md-offset-2 intro-text">
                                <h1>
                                    {props.data ? props.data.title : "Loading"}
                                    <span></span>
                                </h1>
                                <p>{props.data ? props.data.paragraph : "Loading"}</p>

                                <div style={{height: "100px"}}>
                                    <div style={{
                                        paddingTop: "20px",
                                        borderRadius: "10px",
                                        width: "70%",
                                        position: "relative",
                                        left: "15%",
                                        marginTop: "20px",
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
                                    }}>{props.data.code}
                                </pre>

                                        <button style={{
                                            position: "absolute",
                                            left: "90%",
                                            top: "0%",
                                            backgroundColor: props.data.codeBGColor,
                                            color: "#ffffff",
                                            borderRadius: "10px",
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


                                <div style={{width: "100%"}}>
                                    <a
                                        href="docs/built_with_sphinx/html/index.html"
                                        className="btn btn-custom btn-lg page-scroll"
                                    >
                                        Quick Start
                                    </a>{" "}
                                    <a
                                        href="https://github.com/epfl-dlab/multi-level-reasoning-for-code"
                                        className="btn btn-custom btn-lg page-scroll"
                                    >
                                        Github repo
                                    </a>{" "}
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
