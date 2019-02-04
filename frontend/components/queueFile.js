import React, {Component} from 'react'

class QueueFile extends Component {
    render() {
        const {file} = this.props

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

export default QueueFile
