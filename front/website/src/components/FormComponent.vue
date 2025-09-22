<template>
    <div>
        <h1>{{message}}</h1>
    </div>
</template>

<script>
export default {
    name: "FormComponent",
    data(){
        return{
            message:"แบบฟอร์มบันทึกข้อมูลพนังงาน"
        }
    }
}
</script>


<style scoped>
   h1{
    color:green;
   }
</style>