import React, {Component} from 'react'
import ReactDOM from 'react-dom'

class App extends Component {
  constructor(props) {
    super(props)
    this.state = {
      url: "",
      category: "",
      status: {
        urls: []
      }
    }
    this.onSubmit = this.onSubmit.bind(this)

    this.statusUpdateIntervalId = null
  }
  componentWillMount() {
    if (!this.statusUpdateIntervalId) {
        this.onTimer()
        this.statusUpdateIntervalId = setInterval(this.onTimer.bind(this), 5000)
    }
  }
  onSubmit() {
    const body = new URLSearchParams()
    body.append('mega_url', this.state.url)
    const category = this.state.category
    if (category) {
      body.append('category', category)
    }

    fetch('/api/urls/', {
      body: body,
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
    this.statusUpdateIntervalId = null
  }

  render() {
    const urls = this.state.status.urls || []

    return (
      <div>
        <div>
          <textarea name="media" onChange={e => this.setState({url: e.target.value})} />
          <input name="category" type="text" onChange={e => this.setState({category: e.target.value})} />
          <button onClick={this.onSubmit} type="button">Submit</button>
        </div>
        <div>
          {urls.map(url => (<div key={url.id}>{this.renderUrl(url)}</div>))}
        </div>
      </div>
    );
  }

  renderUrl(url) {
    if (url.status == 'DONE') {
      return (<div>{url.url} [finished]</div>)
    }

    return (
      <div>
        {url.url}
        <ul>{url.files.map(file => (<li key={file.file_id}>{this.renderFile(file)}</li>))}</ul>
      </div>
    )
  }

  renderFile(file) {
    if (file.is_finished) {
      return (<div>{file.path} [finished] </div>)
    }

    return (
      <div>
        {file.path}
        <p>{Math.round(file.mean_speed / 1024)} kbps</p>
        <p>{Math.round((file.transferred_bytes / file.total_bytes) * 100)}% finished</p>
        <p>is downloading: {file.is_downloading ? "yes" : "no"}</p>
      </div>
    )
  }
}

ReactDOM.render(
  <App />,
  document.getElementById('app')
);
