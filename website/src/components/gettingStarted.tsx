import React, { useState, useEffect } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

// ... (previous imports)

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

  return (
    <div id="getting_started" className="container">
      <div className="text-center col-md-10 col-md-offset-1 section-title">
        <h2 className="display-3">Examples</h2>
      </div>
      <div className="row">
        <div className="col-md-4 d-flex flex-column">
          <div
            className="mb-3 title"
            style={{
              fontSize: '1.5em',
              fontWeight: 'bold',
              color: '#333', // Match the color with the active list item
              marginBottom: '10px', // Add margin for separation
            }}
          >
            {props.data.title}
          </div>
          <div className="list-group flex-grow-1">
            {['code_1', 'code_2', 'code_3'].map((codeKey, index) => (
              <a
                href="#"
                key={codeKey}
                className={`list-group-item list-group-item-action ${activeOption === codeKey ? 'active' : ''}`}
                onClick={(e) => handleOptionClick(props.data[codeKey], codeKey, e)}
                style={{
                  backgroundColor: activeOption === codeKey ? '#007bff' : 'inherit',
                  color: activeOption === codeKey ? '#fff' : '#1e90ff',
                  fontWeight: 'bold',
                  fontSize: '1.2em',
                  borderRadius: '5px',
                  cursor: 'pointer',
                  marginBottom: '5px',
                }}
              >
                {props.data[`text_${index + 1}`]}
              </a>
            ))}
          </div>
        </div>
        <div className="col-md-8" style={{ maxHeight: '800px', overflowY: 'auto' }}>
          <SyntaxHighlighter language="python" style={vscDarkPlus}>
            {activeCode}
          </SyntaxHighlighter>
        </div>
      </div>
    </div>
  );
};


