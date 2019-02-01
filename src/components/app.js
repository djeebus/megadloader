import React, { Component } from "react";
import {connect} from 'react-redux'
import PropTypes from 'prop-types'

import AddUrl from '../components/addUrl'
import {refreshQueue} from "../actions";

class App extends Component {
    constructor(props) {
        super(props)
        this.state = {
            status: {
                urls: []
            }
        }

        this.statusUpdateIntervalId = null
    }

    componentWillMount() {
        if (!this.statusUpdateIntervalId) {
            this.props.onTimer()
            this.statusUpdateIntervalId = setInterval(() => {
                this.props.onTimer();
            }, 5000)
        }
    }

    componentWillUnmount() {
        clearInterval(this.statusUpdateIntervalId)
        this.statusUpdateIntervalId = null
    }

    render() {
        const urls = this.props.queue || []
        return (
            <div>
                <AddUrl />
                <div>
                    {urls.map(url => (<div key={url.id}>{this.renderUrl(url)}</div>))}
                </div>
            </div>
        )
    }

    renderUrl(url) {
        if (url.status === 'DONE') {
            return (<div>{url.url} [finished]</div>)
        }

        return (
            <div>
                {url.url}
                <ul>{url.files.map(file => (<li key={file.file_id}>{App.renderFile(file)}</li>))}</ul>
            </div>
        )
    }

    static renderFile(file) {
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

const filePropType = PropTypes.shape({
    file_id: PropTypes.isRequired,
    is_finished: PropTypes.bool.isRequired,
    mean_speed: PropTypes.number.isRequired,
    transferred_bytes: PropTypes.number.isRequired,
    is_downloading: PropTypes.bool.isRequired,
})

const queueItemPropType = PropTypes.shape({
    url: PropTypes.string.isRequired,
    files: PropTypes.arrayOf(filePropType).isRequired,
})

App.propTypes = {
    onTimer: PropTypes.func.isRequired,
    queue: PropTypes.arrayOf(queueItemPropType).isRequired,
}

function mapStateToProps(state) {
    return {queue: state.queue.items}
}

function mapDispatchToProps(dispatch) {
    return {onTimer: () => dispatch(refreshQueue())}
}

export default connect(mapStateToProps, mapDispatchToProps)(App)