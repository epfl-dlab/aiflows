import React, { useState, useEffect } from 'react';

export const GettingStarted = (props: any) => {
  const [activeCode, setActiveCode] = useState(props.data.code_1);
  const [activeOption, setActiveOption] = useState('code_1');

  useEffect(() => {
    // Update the active code based on the initial active option
    setActiveCode(props.data[activeOption]);
  }, [activeOption, props.data]);

  const handleOptionClick = (codeSnippet: string, optionKey: string, event: any) => {
    event.preventDefault();
    setActiveCode(codeSnippet);
    setActiveOption(optionKey);
  };

  const isActiveOption = (optionKey: string) => {
    return activeOption === optionKey;
  };

  // ToDo:
    // 1. Make the height of the code block match the height of max code block (so that it doesn't jump around)
    // 2. Make the code block black and python syntax highlighted
    // 3. Title on the left look like a title

  return (
    <div id="getting_started">
      <div className="container">
        <div className="text-center col-md-10 col-md-offset-1 section-title">
          <h2>Example</h2>
        </div>
      <div className="row">
        <div className="col-md-4 d-flex flex-column">
          <div className="mb-3">{props.data.title}</div>
          <div className="list-group flex-grow-1">
            {['code_1', 'code_2', 'code_3'].map((codeKey, index) => (
              <a href="#"
                 key={codeKey}
                 className={`list-group-item list-group-item-action ${isActiveOption(codeKey) ? 'active' : ''}`}
                 onClick={(e) => handleOptionClick(props.data[codeKey], codeKey, e)}>
                {props.data[`text_${index + 1}`]}
              </a>
            ))}
          </div>
        </div>
        <div className="col-md-8">
            <pre>
              <code className={props.data.language}>
                {activeCode}
              </code>
            </pre>
        </div>
      </div>
    </div>
    </div>
  );
};
