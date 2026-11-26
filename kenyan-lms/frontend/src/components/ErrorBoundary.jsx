import { Component } from "react";
import RollingLabel from "./RollingLabel";

export default class ErrorBoundary extends Component {
  constructor(props) { super(props); this.state = { error: null }; }
  static getDerivedStateFromError(error) { return { error }; }
  render() {
    if (this.state.error) {
      return (
        <div className="panel panel-pad" role="alert" style={{ margin: "2rem" }}>
          <h2>Something went wrong</h2>
          <p className="mono">{String(this.state.error.message || this.state.error)}</p>
          <button onClick={() => this.setState({ error: null })}>
            <RollingLabel>Try again</RollingLabel>
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
