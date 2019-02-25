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

        this.onSelectCategory = this.onSelectCategory.bind(this)
    }

    onSelectCategory(e) {
        if (e.target == null) {
            this.setState({category: ''})
            return;
        }

        this.setState({category: e.target.value})
    }

    render() {
        return (
            <div>
                <div>
                    URL:
                    <textarea name="media" onChange={e => this.setState({url: e.target.value})} />
                </div>
                <div>
                    Category:
                    <select onChange={this.onSelectCategory}>
                        <option/>
                        {this.props.categories.map((c) => (
                            <option key={c.category_id} value={c.name}>{c.name}</option>
                        ))}
                    </select>
                </div>
                <button onClick={() => this.props.onSubmit(this.state.url, this.state.category)} type="button">Submit</button>
            </div>
        )
    }
}

function mapStateToProps(state) {
    return {
        categories: state.categories.items,
        queue: state.queue.items,
    }
}

function mapDispatchToProps(dispatch) {
    return {onSubmit: (megaUrl, category) => dispatch(addMegaLink(megaUrl, category))}
}

export default connect(mapStateToProps, mapDispatchToProps)(AddUrl)
