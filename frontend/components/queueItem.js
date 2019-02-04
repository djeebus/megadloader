import React, {Component} from 'react'

import QueueFile from './queueFile'
import RemoveUrl from './removeUrl'

class QueueItem extends Component {
    render() {
        const {item} = this.props

        return (
            <div>
                {item.url} [{item.status}] <RemoveUrl queue_id={item.queue_id} />
                {item.files.map(file => (<QueueFile key={file.file_id} file={file} />))}
            </div>
        )
    }
}

export default QueueItem
