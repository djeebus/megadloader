import React, {Component} from 'react'
import ReactDOM from 'react-dom'

export default class App extends Component {
  constructor(props) {
    super(props)
    this.state = {
      value: "",
      data: []
    }
    this.onChange = this.onChange.bind(this)
    this.onSubmit = this.onSubmit.bind(this)
  }
  onChange(e) {
    let value = e.target.value
    this.setState({
      value
    })
  }
  onSubmit() {
    fetch('/api/urls/', {
      body: "mega_url=" + this.state.value,
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    }).then(results => {
      return results.json()
    }).then(data => {
      console.log("data: ", data)
    }, err => {
      console.log("err: ", err)
    })
  }
  render() {
    return (
      <div>
        <input onChange={this.onChange} type="text" name="media"/>
        <button onClick={this.onSubmit} type="button">Submit</button>
      </div>
    );
  }
}

  ReactDOM.render(
    <App />,
    document.getElementById('app')
  );