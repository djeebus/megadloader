import React, {Component} from 'react'
import {connect} from 'react-redux'
import {addMegaLink} from "../actions";

class AddUrl extends Component {
    constructor(props) {
        super(props)

        this.state = {
            url: "",
            category: "",
        }
    }

    render() {
        return (
            <div>
                <div>URL: <textarea name="media" onChange={e => this.setState({url: e.target.value})} /></div>
                <div>Category: <input name="category" type="text" onChange={e => this.setState({category: e.target.value})} /></div>
                <button onClick={() => this.props.onSubmit(this.state.url, this.state.category)} type="button">Submit</button>
            </div>
        )
    }
}

function mapStateToProps(state) {
    return {queue: state.queue.items}
}

function mapDispatchToProps(dispatch) {
    return {onSubmit: (megaUrl, category) => dispatch(addMegaLink(megaUrl, category))}
}

export default connect(mapStateToProps, mapDispatchToProps)(AddUrl)