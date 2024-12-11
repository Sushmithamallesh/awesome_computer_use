# TODO
- The problem I am facing is abput types I think. How to gracefully handle this?
- Add a stop button to the Streamlit app


Checklist:
- [x] Message to be sent properly
- [x] Proper helicone integration
- [x] Get a single response from Claude
- [x] Screenshot handling
- [] Define basic computer tools now
- [] Check the body you are sending to Claude
- [] Check the response you are getting from Claude
- [] All sort of optimisation look at the example directory look at everything
- [] What the heck is this?     """
    Set cache breakpoints for the 3 most recent turns
    one cache breakpoint is left for tools/system prompt, to be shared across sessions
    """
- [] Add a stop button to the Streamlit app



Type management: 
UI Message (lightweight) 
  → Convert to Claude Message (API type)
  → API Call
  → Response
  → Convert back to UI Message (lightweight)

Potentially Missing/To Consider:
Error Handling
  Tool execution errors
  Claude API errors
  Browser crashes
State Management
  Browser session persistence
  Tool state cleanup
  Message history management
Tool Response Processing
  Screenshot handling
  Large output handling
  Tool result formatting