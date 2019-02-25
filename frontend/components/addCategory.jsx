import React, { Component } from 'react'
import { connect } from 'react-redux'
import { addCategory } from "../actions";

class AddCategory extends Component {
    constructor(props) {
        super(props)

        this.onCategoryChange = this.onCategoryChange.bind(this)
        this.onSubmit = this.onSubmit.bind(this)
    }

    onCategoryChange(e) {
        this.setState({ text: e.target.value })
    }

    onSubmit() {
        this.props.onSubmit(this.state.text)
    }

    render() {
        return (
            <div>
                <label htmlFor="category-name">Category Name: </label>
                <input id="category-name" type="text" onChange={this.onCategoryChange} />
                <button type="button" onClick={this.onSubmit}>Create Category</button>
            </div>
        )
    }
}

function mapStateToProps(state) {
    return {}
}

function mapDispatchToProps(dispatch) {
    return { onSubmit: (name) => dispatch(addCategory(name)) }
}

export default connect(mapStateToProps, mapDispatchToProps)(AddCategory)
