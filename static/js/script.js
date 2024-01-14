const add_product = (event)=>{
    event.preventDefault()
    const name = document.getElementsByName('pname')[0].value;
    const image_url = document.getElementsByName('pimage')[0].value;
    const price = document.getElementsByName('pprice')[0].value;
    const category = document.getElementsByName('pcategory')[0].value;
    const color = document.getElementsByName('pcolor')[0].value;
    const xs_qty = document.getElementsByName('pxs')[0].value;
    const s_qty = document.getElementsByName('ps')[0].value;
    const m_qty = document.getElementsByName('pm')[0].value;
    const l_qty = document.getElementsByName('pl')[0].value;
    const xl_qty = document.getElementsByName('pxl')[0].value;
    const xxl_qty = document.getElementsByName('pxxl')[0].value;

    const data = {
        name,
        image_url,
        price,
        category,
        color,
        xs_qty,
        s_qty,
        m_qty,
        l_qty,
        xl_qty,
        xxl_qty
    };

    fetch('/add', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => {
        // Handle response from backend if needed
        console.log('Product added successfully');
    })
    .catch(error => {
        console.error('Error adding product:', error);
    });

}

const addToCart = (id)=>{
    const sizes = document.getElementsByName('size')
    let size_value = ''
    sizes.forEach((size)=>{
        if (size.checked){
            size_value=size.value
        }
    })
    console.log(size_value)
    const data = {
        pid:id,
        size: size_value
    };

    fetch('/add-to-cart', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body:JSON.stringify(data)
    })
    .then(response => {
        console.log('Product added to cart')
        // console.log(response)
        window.location.reload();
    })
    .catch(error=>{
        console.error('Error adding product to cart', error);
    });
}
