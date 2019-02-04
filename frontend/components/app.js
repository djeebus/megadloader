import React, { Component } from "react";
import {connect} from 'react-redux'
import PropTypes from 'prop-types'

import AddUrl from '../components/addUrl'
import QueueItem from './queueItem'
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
                    {urls.map(url => (<QueueItem key={url.queue_id} item={url} />))}
                </div>
            </div>
        )
    }
}

const filePropType = PropTypes.shape({
    file_id: PropTypes.isRequired,
    is_finished: PropTypes.bool.isRequired,
    mean_speed: PropTypes.number,
    transferred_bytes: PropTypes.number.isRequired,
    is_downloading: PropTypes.bool.isRequired,
})

const queueItemPropType = PropTypes.shape({
    files: PropTypes.arrayOf(filePropType).isRequired,
    queue_id: PropTypes.string.isRequired,
    url: PropTypes.string.isRequired,
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
