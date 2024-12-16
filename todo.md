# TODO


Checklist:
- [x] Message to be sent properly
- [x] Proper helicone integration
- [x] Get a single response from Claude
- [x] Screenshot handling
- [x] Give the tool to claude. Check if its working first. Send a screenshot tool check on helicone
- [] add a non computer tool
- [] Define basic computer tools now
- [] Check how to set the pages width and height for the whole scaling coordinates thing
- [] Check the body you are sending to Claude. Are you properly including the tool callls?
- [] Check the response you are getting from Claude
- [] All sort of optimisation look at the example directory look at everything: example caching optimisation
- [] What the heck is this?     
"""
    Set cache breakpoints for the 3 most recent turns
    one cache breakpoint is left for tools/system prompt, to be shared across sessions
"""
- [] Add a stop button to the Streamlit app
- [] Rest max retries to 3 for now

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