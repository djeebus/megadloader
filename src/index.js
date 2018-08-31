import React, {Component} from 'react'
import ReactDOM from 'react-dom'

export default class App extends Component {
  constructor(props) {
    super(props)
    this.state = {
      value: "",
      data: [],
      status: {
        urls: []
      }
    }
    this.onChange = this.onChange.bind(this)
    this.onSubmit = this.onSubmit.bind(this)

    this.statusUpdateIntervalId = null
  }
  componentWillMount() {
    if (!this.statusUpdateIntervalId) {
      setInterval(this.onTimer.bind(this), 1000)
    }
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

  onTimer() {
    fetch('/api/status')
      .then(res => res.json())
      .then(status => this.setState({status}))
  }

  componentWillUnmount() {
    clearInterval(this.statusUpdateIntervalId)
  }

  render() {
    const urls = this.state.status.urls || []

    return (
      <div>
        <div>
          <textarea onChange={this.onChange} name="media"/>
          <button onClick={this.onSubmit} type="button">Submit</button>
        </div>
        <div>
          {urls.map(url => (<div key={url.id}>{this.renderUrl(url)}</div>))}
        </div>
      </div>
    );
  }

  renderUrl(url) {
    return (
      <div>
        {url.url}
        <ul>{url.files.map(file => (<li key={file.file_id}>{this.renderFile(file)}</li>))}</ul>
      </div>
    )
  }

  renderFile(file) {
    return (
      <div>{file.path} = {file.status}</div>
    )
  }
}

ReactDOM.render(
  <App />,
  document.getElementById('app')
);