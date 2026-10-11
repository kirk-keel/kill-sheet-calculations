// Runs the killsheet Python package (Pyodide) in the background (a module worker), so the page
// stays responsive while a sheet is calculated. The page sends
// {id, call: "example_wells" | "calculate", args} and gets back {id, result} or {id, error}.
import {loadPyodide} from "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs";

const ready = (async () => {
  const pyodide = await loadPyodide();
  const zip = await (await fetch("killsheet.zip")).arrayBuffer();
  pyodide.unpackArchive(zip, "zip");              // the killsheet package and the example wells
  pyodide.runPython(await (await fetch("app.py")).text());
  return pyodide;
})();

self.onmessage = async ({data: {id, call, args}}) => {
  try {
    const pyodide = await ready;
    self.postMessage({id, result: pyodide.globals.get(call)(...args)});
  } catch (error) {
    self.postMessage({id, error: String(error)});
  }
};
