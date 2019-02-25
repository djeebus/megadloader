import React, {Component} from 'react'
import {connect} from 'react-redux'
import {removeQueueItem} from '../actions'

class RemoveUrl extends Component {
    render() {
        const {queue_id} = this.props

        return <button onClick={() => this.props.remove(queue_id)}>Remove</button>
    }
}

function mapDispatchToProps(dispatch) {
    return {remove: (queueId) => dispatch(removeQueueItem(queueId))}
}

export default connect(null, mapDispatchToProps)(RemoveUrl)
