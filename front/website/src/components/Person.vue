<template>
    <div>
        <h1>ชื่อ : {{name}} เงินเดือน : {{salary}}</h1>
    </div>
</template>

<script>
export default {
    name:"Person",
    data(){
        return{
            message:"ข้อมูลพนักงานแต่ละคน"
        }
    },
    props:["name","salary"]
}
</script>

<style scoped>
   h1{
    color:red;
   }
</style>